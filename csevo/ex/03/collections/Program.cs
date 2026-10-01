// 슬라이드 p3-v2-collections — BCL 의 제네릭 컬렉션, C# 2.0
using System;
using System.Collections;
using System.Collections.Generic;

class App
{
    static void Main()
    {
        Hashtable old = new Hashtable();
        old["one"] = 1;
        int a = (int)old["one"];          // cast back from object
        Dictionary<string, int> map = new Dictionary<string, int>();
        map["one"] = 1;
        int b = map["one"];               // already an int
        Console.WriteLine(a + b);

        Console.WriteLine(old["two"] == null);    // missing: null
        int v;
        Console.WriteLine(map.TryGetValue("two", out v) + " " + v);
        try
        {
            Console.WriteLine(map["two"]);        // missing: throws
        }
        catch (KeyNotFoundException e)
        {
            Console.WriteLine(e.GetType().Name);
        }
    }
}
