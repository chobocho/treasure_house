// 슬라이드 p2-v1_2-runtime — 열거자와 IDisposable, C# 1.2
using System;
using System.Collections;

class App
{
    static void Show(string what, object e)
    {
        string type = e.GetType().Name.PadRight(26);
        Console.WriteLine(what.PadRight(10) + type
            + "IDisposable=" + (e is IDisposable));
    }

    static string Bases(Type t)
    {
        Type[] all = t.GetInterfaces();
        string[] names = new string[all.Length];
        for (int i = 0; i < all.Length; i++) names[i] = all[i].Name;
        Array.Sort(names);
        return t.Name + " extends [" + String.Join(", ", names) + "]";
    }

    static void Main()
    {
        Console.WriteLine(Bases(typeof(IEnumerator)));
        Console.WriteLine(Bases(Type.GetType(
            "System.Collections.Generic.IEnumerator`1")));
        Show("ArrayList", new ArrayList().GetEnumerator());
        Show("Hashtable", new Hashtable().GetEnumerator());
        Show("int[]", new int[1].GetEnumerator());
        Show("string", "ab".GetEnumerator());
    }
}
