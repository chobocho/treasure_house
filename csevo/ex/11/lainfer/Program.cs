// 슬라이드 p11-v10-la-infer — 자연 형식과 형식 유추, C# 10.0
using System;

class App
{
    static string Run<T>(T d) where T : Delegate => typeof(T).Name;
    static string Two<T>(T a, T b) => typeof(T).Name;
    static int Len(string s) => s.Length;

    static void Main()
    {
        // best common type of two lambdas: Func<string, int>[]
        var fs = new[] { (string s) => s.Length, (string s) => 0 };
        Console.WriteLine(fs.GetType().Name + " " + fs[0]("abc"));
        // T : Delegate is inferred from the lambda's natural type
        Console.WriteLine(Run(() => 42) + " " + Run(Len));
        // a lambda and a method group with the same signature
        Console.WriteLine(Two((string s) => s.Length, Len));
        var arr = new[] { Len, Len };     // method groups as well
        Console.WriteLine(arr.GetType().Name);
#if BAD
        bool flip = true;
        var pick = flip ? (int a) => a : (int b) => -b;
        _ = () => 1;                      // discards: no natural type
        var g = Two((int a) => a, (long b) => b);
#endif
    }
}
