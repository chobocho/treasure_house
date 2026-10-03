// 슬라이드 p12-v11-sa-il — 형식 매개변수를 거친 호출의 IL, C# 11.0
using System;
using System.Numerics;
using System.Reflection;

class App
{
    static T Next<T>(T x) where T : INumber<T> => x + T.One;

    // Interface-typed parameter vs constrained type parameter
    static bool PosI(INumber<int> x, int z) => x.CompareTo(z) > 0;
    static bool PosG<T>(T x, T z) where T : INumber<T> =>
        x.CompareTo(z) > 0;
    static bool CallI() => PosI(5, 0);
    static bool CallG() => PosG(5, 0);

    static void Show(string name)
    {
        Console.WriteLine(name + ":");
        Il.Dump(typeof(App).GetMethod(name,
            BindingFlags.NonPublic | BindingFlags.Static));
    }

    static void Main(string[] args)
    {
        if (args.Length == 0)
        {
            Show("Next");
            Console.WriteLine(Next(41) + " " + Next(0.5));
            return;
        }
        foreach (string n in new[] { "CallI", "PosI", "CallG", "PosG" })
            Show(n);
    }
}
