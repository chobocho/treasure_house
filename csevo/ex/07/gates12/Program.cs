// 슬라이드 p7-v6-gates-demo — 게이트 열두 개를 한 파일에, C# 6.0
using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using static System.Math;                  // using static

class C
{
    public int A { get; } = 1;             // get-only, initializer
    public int B { get; set; } = 2;        // initializer
    public int Twice() => A * 2;           // => method
    public int Sum => A + B;               // => property
    public int this[int i] => i + A;       // => indexer
}

class App
{
    static async Task<string> Run(C c)
    {
        string log = "";
        try { throw new Exception("x"); }
        catch (Exception e) when (e.Message == "x") // filter
        { await Task.Yield(); log += "c"; }         // await in catch
        finally { await Task.Yield(); }             // await in finally
        var d = new Dictionary<string, int> { ["k"] = c.Sum };
        string s = null;
        return $"{nameof(c)} {s?.Length} {Abs(-c[d["k"]])} {log}";
    }

    static void Main()
    {
        Console.WriteLine(Run(new C()).Result);
    }
}
