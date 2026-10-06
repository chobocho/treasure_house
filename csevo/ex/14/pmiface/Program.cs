// 슬라이드 p14-v13-pm-iface — 인터페이스 params 가 받는 형식, C# 13
using System;
using System.Collections.Generic;

class Program
{
    static string E(params IEnumerable<int> xs) => Name(xs);
    static string RC(params IReadOnlyCollection<int> xs) => Name(xs);
    static string RL(params IReadOnlyList<int> xs) => Name(xs);
    static string C(params ICollection<int> xs) => Name(xs);
    static string L(params IList<int> xs) => Name(xs);

    static string Name(object o) => o.GetType().Name + " "
        + (o is ICollection<int> c ? "ReadOnly=" + c.IsReadOnly : "");

    static void Main()
    {
        Console.WriteLine("IEnumerable          3: " + E(1, 2, 3));
        Console.WriteLine("IEnumerable          0: " + E());
        Console.WriteLine("IReadOnlyCollection  3: " + RC(1, 2, 3));
        Console.WriteLine("IReadOnlyList        1: " + RL(1));
        Console.WriteLine("ICollection          3: " + C(1, 2, 3));
        Console.WriteLine("IList                0: " + L());
    }
}
