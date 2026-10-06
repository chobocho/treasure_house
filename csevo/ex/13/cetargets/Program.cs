// 슬라이드 p13-v12-ce-targets — 대상 형식과 실제 형식, C# 12
using System;
using System.Collections.Generic;

class Program
{
    static void Show(string target, object o)
    {
        Console.WriteLine(target.PadRight(26) + o.GetType().Name);
    }

    static void Main()
    {
        int[] arr = [1, 2, 3];
        List<int> list = [1, 2, 3];
        IEnumerable<int> e = [1, 2, 3];
        IReadOnlyCollection<int> rc = [1, 2, 3];
        IReadOnlyList<int> rl = [1, 2, 3];
        ICollection<int> c = [1, 2, 3];
        IList<int> l = [1, 2, 3];
        Show("int[]", arr);
        Show("List<int>", list);
        Show("IEnumerable<int>", e);
        Show("IReadOnlyCollection<int>", rc);
        Show("IReadOnlyList<int>", rl);
        Show("ICollection<int>", c);
        Show("IList<int>", l);
    }
}
