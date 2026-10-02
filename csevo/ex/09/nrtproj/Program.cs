// 슬라이드 p9-v8-nrt-optin — 프로젝트 단위로 켜기, C# 8.0
using System;

class App
{
    static void Main()
    {
        string s = null;           // no '#nullable' in this file
        string? t = "set";
        Console.WriteLine((s ?? "null") + " " + t);
    }
}
