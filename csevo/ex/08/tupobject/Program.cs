// 슬라이드 p8-v7-tuple-object — object·dynamic 과 이름, C# 7.0
using System;

class App
{
    static void Main()
    {
        var p = (name: "Kim", age: 30);
        object o = p;
        var back = ((string, int))o;        // unbox: no names
        Console.WriteLine(back.Item1);
        var named = ((string name, int age))o;  // names come back
        Console.WriteLine(named.name);

        dynamic d = p;
        Console.WriteLine(d.Item2);         // the real field
        try
        {
            Console.WriteLine(d.age);       // not in metadata
        }
        catch (Exception e)
        {
            Console.WriteLine(e.GetType().Name);
            Console.WriteLine(e.Message);
        }
    }
}
