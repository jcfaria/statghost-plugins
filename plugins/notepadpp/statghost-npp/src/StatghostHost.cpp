#include "StatghostHost.h"
#include "StatghostPrefs.h"
#include "StatghostProtocol.h"
#include "StatghostBridge.h"

#include <shlwapi.h>
#include <tlhelp32.h>

#include <chrono>
#include <thread>
#include <vector>

namespace
{
    constexpr wchar_t EXE_NAME[] = L"statghost.exe";

    bool isExePath(const std::wstring &path)
    {
        return !path.empty() && ::PathFileExistsW(path.c_str()) != FALSE;
    }

    std::wstring trim(const std::wstring &text)
    {
        std::size_t start = 0;
        while (start < text.size() && (text[start] == L' ' || text[start] == L'\t'))
            ++start;
        std::size_t end = text.size();
        while (end > start && (text[end - 1] == L' ' || text[end - 1] == L'\t'))
            --end;
        return text.substr(start, end - start);
    }

    std::wstring modulePath()
    {
        wchar_t buf[MAX_PATH] = {};
        const DWORD len = ::GetModuleFileNameW(nullptr, buf, MAX_PATH);
        if (len == 0 || len >= MAX_PATH)
            return L"";
        return std::wstring(buf, len);
    }

    std::wstring siblingStatghostExe()
    {
        std::wstring cur = modulePath();
        for (int depth = 0; depth < 8; ++depth)
        {
            const std::size_t slash = cur.find_last_of(L"\\/");
            if (slash == std::wstring::npos)
                break;
            const std::wstring parent = cur.substr(0, slash);
            const std::wstring cand = parent + L"\\statghost\\src\\_out\\" + EXE_NAME;
            if (isExePath(cand))
                return cand;
            cur = parent;
        }
        return L"";
    }

    std::wstring envExe()
    {
        wchar_t buf[MAX_PATH] = {};
        const DWORD len = ::GetEnvironmentVariableW(L"STATGHOST_EXE", buf, MAX_PATH);
        if (len == 0 || len >= MAX_PATH)
            return L"";
        return trim(std::wstring(buf, len));
    }

    std::vector<DWORD> listPids()
    {
        std::vector<DWORD> pids;
        HANDLE snap = ::CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
        if (snap == INVALID_HANDLE_VALUE)
            return pids;

        PROCESSENTRY32W pe = {};
        pe.dwSize = sizeof(pe);
        if (::Process32FirstW(snap, &pe))
        {
            do
            {
                if (_wcsicmp(pe.szExeFile, EXE_NAME) == 0)
                    pids.push_back(pe.th32ProcessID);
            } while (::Process32NextW(snap, &pe));
        }
        ::CloseHandle(snap);
        return pids;
    }

    void clearPidFile(const std::wstring &exe)
    {
        if (exe.empty())
            return;
        wchar_t dir[MAX_PATH] = {};
        wcscpy_s(dir, exe.c_str());
        ::PathRemoveFileSpecW(dir);
        const std::wstring pidPath = std::wstring(dir) + L"\\data\\statghost.pid";
        ::DeleteFileW(pidPath.c_str());
    }

    bool forceStop()
    {
        const auto pids = listPids();
        for (const DWORD pid : pids)
        {
            HANDLE proc = ::OpenProcess(PROCESS_TERMINATE, FALSE, pid);
            if (proc != nullptr)
            {
                ::TerminateProcess(proc, 0);
                ::CloseHandle(proc);
            }
        }

        const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(2);
        while (std::chrono::steady_clock::now() < deadline && !listPids().empty())
            std::this_thread::sleep_for(std::chrono::milliseconds(50));

        clearPidFile(StatghostHost::findExe());
        return listPids().empty();
    }
}

bool StatghostHost::isRunning()
{
    return !listPids().empty();
}

std::wstring StatghostHost::findExe()
{
    const std::wstring cfg = trim(StatghostPrefs::getHostExe());
    if (isExePath(cfg))
        return cfg;

    const std::wstring env = envExe();
    if (isExePath(env))
        return env;

    const std::wstring sib = siblingStatghostExe();
    if (isExePath(sib))
        return sib;

    return L"";
}

bool StatghostHost::start(std::wstring &message)
{
    if (isRunning())
    {
        message = L"already running";
        return true;
    }

    const std::wstring exe = findExe();
    if (exe.empty())
    {
        message = L"STATghost binary not found — Config → Host path or sibling statghost clone";
        return false;
    }

    wchar_t workDir[MAX_PATH] = {};
    wcscpy_s(workDir, exe.c_str());
    ::PathRemoveFileSpecW(workDir);

    STARTUPINFOW si = {};
    si.cb = sizeof(si);
    PROCESS_INFORMATION pi = {};
    std::wstring cmd = L"\"" + exe + L"\"";
    if (!::CreateProcessW(exe.c_str(), cmd.data(), nullptr, nullptr, FALSE,
                          DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
                          nullptr, workDir, &si, &pi))
    {
        message = L"could not start STATghost";
        return false;
    }

    if (pi.hThread != nullptr)
        ::CloseHandle(pi.hThread);
    if (pi.hProcess != nullptr)
        ::CloseHandle(pi.hProcess);

    for (int i = 0; i < 40; ++i)
    {
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
        if (isRunning())
            break;
    }

    if (!isRunning())
    {
        message = L"started but process exited immediately";
        return false;
    }

    message = exe;
    return true;
}

bool StatghostHost::stopGraceful(std::wstring &message)
{
    if (!isRunning())
    {
        clearPidFile(findExe());
        message = L"not running";
        return true;
    }

    const std::wstring payload = StatghostProtocol::makeCommand(L"QUIT");
    if (!StatghostBridge::writeClipboard(payload))
    {
        forceStop();
        message = L"force-stopped (clipboard failed)";
        return true;
    }

    const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(3);
    while (std::chrono::steady_clock::now() < deadline)
    {
        if (!isRunning())
        {
            clearPidFile(findExe());
            message = L"quit";
            return true;
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }

    forceStop();
    message = L"force-stopped (hung Quit)";
    return true;
}
