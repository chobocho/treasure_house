// 슬라이드 p6-v5-better — async 람다와 오버로드 해석, C# 5.0
using System;
using System.Threading.Tasks;

class App
{
    static void M(Func<Task<int>> f) { Console.WriteLine("M int"); }
    static void M(Func<Task<long>> f) { Console.WriteLine("M long"); }

    static void N(Func<Task<int>> f) { Console.WriteLine("N int"); }
    static void N(Func<Task<double>> f) { Console.WriteLine("N dbl"); }

    static void P(Func<Task> f) { Console.WriteLine("P Task"); }
    static void P(Func<Task<int>> f) { Console.WriteLine("P Task<T>"); }

    static void Main()
    {
        short s = 1;
        M(async () => 1);       // int: exact match
        M(async () => 1L);      // long: exact match
        N(async () => s);       // short: no exact match, int is better
        P(async () => { await Task.Yield(); });
        P(async () => { await Task.Yield(); return 1; });
    }
}
