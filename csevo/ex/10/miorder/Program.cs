// 슬라이드 p10-v9-mi-order — 모듈 초기화자와 정적 생성자의 차례, C# 9.0
using System;
using System.Runtime.CompilerServices;

class Config
{
    static Config() { Console.WriteLine("  Config static ctor"); }
    public static int Level = 3;
}

static class Zeta
{
    [ModuleInitializer]
    internal static void InitZ() => Console.WriteLine("InitZ");
}

static class Alpha
{
    [ModuleInitializer]
    internal static void InitA()
    {
        Console.WriteLine("InitA reads Config.Level");
        Console.WriteLine("InitA: " + Config.Level);
    }
}

class App
{
    static App() { Console.WriteLine("App static ctor"); }

    static void Main() => Console.WriteLine("Main");
}
