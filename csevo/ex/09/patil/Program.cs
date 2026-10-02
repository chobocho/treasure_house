// 슬라이드 p9-v8-pat-il — 컴파일러가 부르는 메서드, C# 8.0
using System;
using System.Reflection;

class App
{
    static int Few(string s) => s switch
    {
        "red" => 1, "green" => 2, _ => 0,
    };

    static int Many(string s) => s switch
    {
        "red" => 1, "green" => 2, "blue" => 3, "cyan" => 4,
        "magenta" => 5, "yellow" => 6, "black" => 7, "white" => 8,
        _ => 0,
    };

    static int Stmt(string s)            // the C# 1 switch statement
    {
        switch (s)
        {
            case "red": return 1; case "green": return 2;
            case "blue": return 3; case "cyan": return 4;
            case "magenta": return 5; case "yellow": return 6;
            case "black": return 7; case "white": return 8;
            default: return 0;
        }
    }
    static int Slice(int[] a, string s, Span<int> sp)
    {
        int[] x = a[1..3];
        string t = s[1..];
        Span<int> u = sp[..2];
        return a[^1] + x.Length + t.Length + u.Length;
    }

    static void Main(string[] args)
    {
        string[] names = { "Few", "Many", "Stmt" };
        if (args.Length > 0) names = args;
        foreach (string n in names)
        {
            MethodInfo m = typeof(App).GetMethod(n,
                BindingFlags.NonPublic | BindingFlags.Static);
            Console.WriteLine(n + ":");
            foreach (string c in Il.Calls(m))
                Console.WriteLine("  " + c);
        }
    }
}
