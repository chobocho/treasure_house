// 슬라이드 p12-v11-mgcache-scope — 어떤 변환이 캐시되나, C# 11.0
using System;

static class Ext
{
    public static int Inc(this string s) => s.Length + 1;
}

class App
{
    static T Id<T>(T x) => x;
    int Half(int x) => x / 2;

    static Func<int, int> Static() => Id<int>;
    static Func<int, int> Local()
    {
        static int Neg(int x) => -x;
        return Neg;
    }
    static Func<int, int> Lambda() => x => x + 1;
    static Func<int, int> Inst(App a) => a.Half;
    static Func<int> Extn(string s) => s.Inc;

    static void Show(string what, Delegate p, Delegate q) =>
        Console.WriteLine($"{what,-22} {ReferenceEquals(p, q)}");

    static void Main()
    {
        App a = new App();
        Show("static generic Id<int>", Static(), Static());
        Show("static local function", Local(), Local());
        Show("lambda x => x + 1", Lambda(), Lambda());
        Show("instance a.Half", Inst(a), Inst(a));
        Show("extension s.Inc", Extn("ab"), Extn("ab"));
    }
}
