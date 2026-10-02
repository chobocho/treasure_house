// 슬라이드 p10-v9-modinit — 모듈 초기화자, C# 9.0
using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;

static class Registry
{
    public static readonly List<string> Names = new List<string>();
}

// Imagine a source generator wrote this class.
static class GeneratedSetup
{
    [ModuleInitializer]
    internal static void Init()
    {
        Console.WriteLine("module initializer");
        Registry.Names.Add("parser");
        Registry.Names.Add("printer");
    }
}

class App
{
    static void Main()
    {
        // Nobody called Init().
        Console.WriteLine("Main: " + string.Join(", ", Registry.Names));
    }
}
