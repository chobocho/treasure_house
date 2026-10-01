// 슬라이드 p2-v1-typeof — typeof 와 GetType, C# 1.0
using System;
using System.Collections;

enum Color { Red }

class App
{
    static void Main()
    {
        Console.WriteLine(typeof(int).FullName);
        Console.WriteLine(typeof(int[,]).Name);
        Console.WriteLine(typeof(void).FullName);
        Console.WriteLine(typeof(Color).BaseType.Name);

        object x = new ArrayList();               // static type: object
        Console.WriteLine(x.GetType().Name);      // run-time type
        Console.WriteLine(x.GetType() == typeof(ArrayList));
        Console.WriteLine(x.GetType() == typeof(object));
        Console.WriteLine(x is object);

        Type t = typeof(string);
        Console.WriteLine(t.IsClass + " " + t.IsSealed);
        Console.WriteLine(ReferenceEquals(typeof(int), 1.GetType()));
    }
}
