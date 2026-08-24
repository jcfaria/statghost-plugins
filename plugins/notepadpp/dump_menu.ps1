Add-Type @'
using System; using System.IO; using System.Runtime.InteropServices; using System.Text;
public static class T {
  public const int WM_USER=0x0400; public const int NPPMSG=WM_USER+1000; public const int NPPM_GETMENUHANDLE=NPPMSG+25;
  public const uint MF_BYPOSITION=0x400;
  [DllImport("user32.dll")] public static extern IntPtr SendMessage(IntPtr h,int m,IntPtr w,IntPtr l);
  [DllImport("user32.dll")] public static extern int GetMenuItemCount(IntPtr h);
  [DllImport("user32.dll",CharSet=CharSet.Unicode)] public static extern int GetMenuString(IntPtr h,uint i,StringBuilder s,int c,uint f);
  [DllImport("user32.dll")] public static extern IntPtr GetSubMenu(IntPtr h,int p);
  [DllImport("user32.dll")] public static extern uint GetMenuItemID(IntPtr h,int p);
  public static void Dump(IntPtr menu,int d,StringBuilder sb) {
    if(menu==IntPtr.Zero)return;
    int n=GetMenuItemCount(menu);
    for(int i=0;i<n;i++){
      var t=new StringBuilder(256); int len=GetMenuString(menu,(uint)i,t,256,MF_BYPOSITION);
      uint id=GetMenuItemID(menu,i);
      IntPtr sub=GetSubMenu(menu,i);
      sb.AppendLine(string.Format("{0}[{1}] id={2} len={3} sub={4} text={5}", new string(' ',d*2), i, id, len, sub!=IntPtr.Zero, t.ToString()));
      if(sub!=IntPtr.Zero) Dump(sub,d+1,sb);
    }
  }
}
'@
$npp='c:\Users\jcfaria\Documents\Github\statghost-plugins\plugins\notepadpp\.lab\notepad++.exe'
$p=Start-Process -FilePath $npp -PassThru
Start-Sleep 4
$h=[IntPtr]$p.MainWindowHandle
$m=[T]::SendMessage($h,[T]::NPPM_GETMENUHANDLE,[IntPtr]::Zero,[IntPtr]::Zero)
$cnt=[T]::GetMenuItemCount($m)
$out=New-Object System.Text.StringBuilder
for($i=0;$i -lt $cnt;$i++){
  $sb=New-Object System.Text.StringBuilder 256
  [T]::GetMenuString($m,[uint32]$i,$sb,256,[T]::MF_BYPOSITION)
  if($sb.ToString() -eq 'STATghost'){
    $sg=[T]::GetSubMenu($m,$i)
    [T]::Dump($sg,0,$out)
  }
}
$path='c:\Users\jcfaria\Documents\Github\statghost-plugins\plugins\notepadpp\menu_dump.txt'
[System.IO.File]::WriteAllText($path,$out.ToString())
Stop-Process -Id $p.Id -Force
Get-Content $path
