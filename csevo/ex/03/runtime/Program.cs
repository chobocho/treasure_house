// 슬라이드 p3-v2-runtime — 런타임이 아는 제네릭, C# 2.0
using System;
using System.Collections.Generic;

class App
{
    static void Main()
    {
        Type a = typeof(List<int>);
        Type b = typeof(List<string>);
        Console.WriteLine(a);
        Console.WriteLine(b);
        Console.WriteLine(a == b);

        Type da = a.GetGenericTypeDefinition();
        Type db = b.GetGenericTypeDefinition();
        Console.WriteLine(da);
        Console.WriteLine(da == db);
        Console.WriteLine(a.GetGenericArguments()[0]);
        Console.WriteLine(a.Assembly.GetName().Name);
    }
}
