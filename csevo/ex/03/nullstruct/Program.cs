// 슬라이드 p3-v2-nullable-struct — int? 는 Nullable<int>, C# 2.0
using System;

class App
{
    static void Main()
    {
        Console.WriteLine(typeof(int?) == typeof(Nullable<int>));
        Console.WriteLine(typeof(int?));
        Console.WriteLine(typeof(int?).IsValueType);
        Console.WriteLine(Nullable.GetUnderlyingType(typeof(int?)));
        Type plain = Nullable.GetUnderlyingType(typeof(long));
        Console.WriteLine(plain == null);

        Nullable<int> n = new Nullable<int>(3);
        int? m = 3;
        Console.WriteLine(n == m);
        Console.WriteLine(typeof(int?).GetInterfaces().Length);
        Console.WriteLine(typeof(int).GetInterfaces().Length > 0);
    }
}
