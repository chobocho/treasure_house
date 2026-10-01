// 슬라이드 p0-machine — 이 덱을 돌린 런타임, C# 14
using System;
using System.Runtime.InteropServices;

static class Program
{
    static void Main()
    {
        Console.WriteLine(RuntimeInformation.FrameworkDescription);
        Console.WriteLine(RuntimeInformation.ProcessArchitecture);
        Console.WriteLine(RuntimeInformation.RuntimeIdentifier);
        Console.WriteLine(Environment.Version);
    }
}
