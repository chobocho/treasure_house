// 슬라이드 p4-v3-var-locals — var 와 명시적 형식은 같다, C# 3.0
using System;
using System.Collections.Generic;
using System.Reflection;

class App
{
    static string Explicit()
    {
        int i = 5;
        string s = "Hello";
        double d = 1.0;
        int[] numbers = new int[] { 1, 2, 3 };
        return s + i + d + numbers.Length;
    }

    static string Implicit()
    {
        var i = 5;
        var s = "Hello";
        var d = 1.0;
        var numbers = new int[] { 1, 2, 3 };
        return s + i + d + numbers.Length;
    }

    static void Dump(string name)
    {
        MethodInfo m = typeof(App).GetMethod(name,
            BindingFlags.NonPublic | BindingFlags.Static);
        Console.Write(name + " → " + m.Invoke(null, null) + " :");
        MethodBody body = m.GetMethodBody();
        foreach (LocalVariableInfo v in body.LocalVariables)
            Console.Write(" " + v.LocalType.Name);
        Console.WriteLine();
    }

    static void Main()
    {
        Dump("Explicit");
        Dump("Implicit");
    }
}
