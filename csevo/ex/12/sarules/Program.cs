// 슬라이드 p12-v11-sa-rules — static 멤버의 작은 규칙들, C# 11.0
using System;

interface IOld
{
    static sealed int Answer() => 42;   // "sealed" is now allowed
}

interface IA { static abstract string Name { get; } }
interface IB { static abstract string Name { get; } }

class Both : IA, IB
{
    public static string Name => "both";   // implements both
}

#if CLASS
abstract class K { public static abstract int Z { get; } }
#endif

class App
{
    static string One<T>() where T : IA => T.Name;
#if AMBIG
    static string Two<T>() where T : IA, IB => T.Name;
#endif

    static void Main() =>
        Console.WriteLine(IOld.Answer() + " " + One<Both>());
}
