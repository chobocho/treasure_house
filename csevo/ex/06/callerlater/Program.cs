// 슬라이드 p6-v5-caller-later — 뒤 버전의 문법 안에서, C# 14.0
using System;
using System.Runtime.CompilerServices;

// C# 9 top-level statements, C# 7 local function
Console.WriteLine("top-level      -> " + N.Get());
void Local() { Console.WriteLine("local function -> " + N.Get()); }
Local();
Func<string> f = static () => N.Get();          // C# 9
Console.WriteLine("static lambda  -> " + f());
Console.WriteLine("init accessor  -> " + new Opt { X = 1 }.Got);
Console.WriteLine("primary ctor   -> " + new Box().Tag);
Console.WriteLine("extension prop -> " + 5.Who);

static class N
{
    public static string Get([CallerMemberName] string m = "?")
        => m;
}

class Opt                                        // C# 9 init
{
    public string Got = "";
    public int X { init { Got = N.Get(); } }
}

class Box(string tag)                            // C# 12
{
    public string Tag = tag;
    public Box() : this(N.Get()) { }
}

static class E                                   // C# 14
{
    extension(int i) { public string Who => N.Get(); }
}
