// 슬라이드 p3-v2-nullable-gettype — GetType 의 함정, C# 2.0
using System;

class App
{
    static void Main()
    {
        int? a = 5;
        Console.WriteLine(a.GetType());   // not Nullable`1
        Console.WriteLine(a.ToString() + "|" + a.Equals(5));
        int? n = null;
        Console.WriteLine("[" + n.ToString() + "] " + n.Equals(null));
        Console.WriteLine(n.GetHashCode());
        try
        {
            Console.WriteLine(n.GetType());
        }
        catch (NullReferenceException e)
        {
            Console.WriteLine(e.GetType().Name);
        }
    }
}
