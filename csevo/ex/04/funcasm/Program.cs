// 슬라이드 p4-v3-runtime-func — Func·Action·ExtensionAttribute, C# 3.0
using System;
using System.Runtime.CompilerServices;

class App
{
    static void Show(Type t)
    {
        Console.WriteLine(t.Name + " in " + t.Assembly.GetName().Name);
    }

    static void Main()
    {
        Show(typeof(Action));
        Show(typeof(Action<>));
        Show(typeof(Action<,,,>));
        Show(typeof(Func<>));
        Show(typeof(Func<,>));
        Show(typeof(ExtensionAttribute));
        Show(typeof(System.Linq.Enumerable));

        Func<int, int> sq = x => x * x;
        Action<string> say = s => Console.WriteLine(s);
        say("sq(7) = " + sq(7));
    }
}
