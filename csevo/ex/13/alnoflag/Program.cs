// 슬라이드 p13-v12-al-unsafe — unsafe 를 막은 프로젝트, C# 12.0
using System;
using unsafe P = int*;                 // declared, never used

class App
{
    static void Main() => Console.WriteLine("ok");
}
