// 슬라이드 p3-v2-open-closed — 열린 형식과 닫힌 형식, C# 2.0
using System;
using System.Collections.Generic;

class App
{
    static void Main()
    {
        Type open = typeof(Dictionary<,>);
        Console.WriteLine(open.ContainsGenericParameters);

        Type[] args = new Type[] { typeof(string), typeof(int) };
        Type closed = open.MakeGenericType(args);
        Console.WriteLine(closed.ContainsGenericParameters);
        Console.WriteLine(closed == typeof(Dictionary<string, int>));

        object d = Activator.CreateInstance(closed);
        Console.WriteLine(d is Dictionary<string, int>);
        Console.WriteLine(closed);
    }
}
