// 슬라이드 p12-v11-math-bcl — int 가 구현하는 인터페이스, C# 11.0
using System;
using System.Linq;

class App
{
    static string Nm(Type t) => !t.IsGenericType ? t.Name
        : t.Name.Substring(0, t.Name.IndexOf('`')) + "<"
          + string.Join(",", t.GetGenericArguments().Select(Nm)) + ">";

    static void Main()
    {
        Type[] all = typeof(int).GetInterfaces();
        Console.WriteLine(all.Length + " interfaces on System.Int32");
        foreach (string s in all
            .Select(t => (t.IsPublic ? "  " : "* ") + Nm(t))
            .OrderBy(s => s.Substring(2), StringComparer.Ordinal))
            Console.WriteLine(s);
        Console.WriteLine("(* = not public)");
    }
}
