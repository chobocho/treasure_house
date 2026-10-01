// 슬라이드 p3-v2-runtime-bcl — 언어 기능이 기대는 BCL 형식, C# 2.0
using System;
using System.Collections.Generic;

class App
{
    static void Show(Type t)
    {
        Type[] ifs = t.GetInterfaces();
        string[] names = new string[ifs.Length];
        for (int i = 0; i < ifs.Length; i++)
        {
            names[i] = ifs[i].Name;
        }
        Array.Sort(names, StringComparer.Ordinal);
        Console.WriteLine(t.Name + ": " + string.Join(", ", names));
    }

    static void Main()
    {
        Show(typeof(IEnumerable<>));      // foreach, iterators
        Show(typeof(IEnumerator<>));      // iterators
        Show(typeof(Nullable<>));         // int?
        Console.WriteLine(typeof(Nullable<>).IsValueType);
        Console.WriteLine(typeof(Comparer<>).Namespace);
    }
}
