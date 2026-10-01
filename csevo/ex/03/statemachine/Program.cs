// 슬라이드 p3-v2-iterator-lowering — 컴파일러가 만든 클래스, C# 2.0
using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;

class App
{
    static bool ran;

    static IEnumerable<int> Seq()
    {
        ran = true;
        yield return 1;
    }

    static void Main()
    {
        IEnumerable<int> s = Seq();
        Type t = s.GetType();
        Console.WriteLine("body ran: " + ran);
        Console.WriteLine("nested in " + t.DeclaringType.Name);
        Console.WriteLine("sealed class " + (t.IsClass && t.IsSealed));
        Type cg = typeof(CompilerGeneratedAttribute);
        Console.WriteLine("generated " + t.IsDefined(cg, false));
        Type[] ifs = t.GetInterfaces();
        string[] names = new string[ifs.Length];
        for (int i = 0; i < ifs.Length; i++) names[i] = ifs[i].Name;
        Array.Sort(names, StringComparer.Ordinal);
        Console.WriteLine(string.Join(", ", names));

        IEnumerator<int> e = s.GetEnumerator();
        e.MoveNext();
        Console.WriteLine("body ran: " + ran);
    }
}
