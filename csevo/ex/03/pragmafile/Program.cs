// 슬라이드 p3-v2-pragma-file — 다른 파일에는 닿지 않는다, C# 2.0
using System;

partial class App
{
    static void Main()
    {
        int y;                           // another file: warned
        Quiet();
        Console.WriteLine("ok");
    }
}
