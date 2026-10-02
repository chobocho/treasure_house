// 슬라이드 p7-v6-interp-await — 구멍에 await 가 있으면, C# 6.0
using System;
using System.Threading.Tasks;

class Loud
{
    readonly string name;
    public Loud(string name) { this.name = name; }
    public override string ToString()
    {
        Console.WriteLine("  ToString " + name);
        return name;
    }
}

class App
{
    static Loud Make(string name)
    {
        Console.WriteLine("  eval     " + name);
        return new Loud(name);
    }

    static async Task<string> Run()
    {
        Console.WriteLine("no await:");
        string s = $"{Make("a")}-{Make("b")}";
        Console.WriteLine("with await:");
        string t = $"{Make("c")}-{await Task.FromResult(Make("d"))}";
        return s + " " + t;
    }

    static void Main()
    {
        Console.WriteLine(Run().Result);
    }
}
