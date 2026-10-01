// 슬라이드 p4-v3-et-codedata — 같은 람다를 코드로, 데이터로, C# 3.0
using System;
using System.Linq.Expressions;
using System.Reflection;

class Program
{
    static void Main()
    {
        Func<int, int> del = x => x + 1;                // code
        Expression<Func<int, int>> exp = x => x + 1;    // data
        Func<int, int> del2 = exp.Compile();

        Console.WriteLine("del(1) = " + del(1)
                          + ", del2(1) = " + del2(1));
        Show("del ", del.Method);
        Show("del2", del2.Method);
    }

    static void Show(string name, MethodInfo m)
    {
        Console.WriteLine(name + ": " + m.Name + " in "
            + (m.DeclaringType == null ? "(no type)"
                                       : m.DeclaringType.FullName)
            + ", " + m.GetType().Name);
    }
}
