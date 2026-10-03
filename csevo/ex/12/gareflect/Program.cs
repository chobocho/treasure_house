// 슬라이드 p12-v11-genattr-reflect — 리플렉션으로 읽기, C# 11.0
using System;
using System.Reflection;

[AttributeUsage(AttributeTargets.Class, AllowMultiple = true)]
class TagAttribute<T> : Attribute { }

[Tag<int>, Tag<string>]
class Item { }

class App
{
    static void Main()
    {
        Type t = typeof(Item);
        Console.WriteLine(t.GetCustomAttribute<TagAttribute<int>>());
        Console.WriteLine(t.IsDefined(typeof(TagAttribute<string>)));
        Console.WriteLine(t.IsDefined(typeof(TagAttribute<long>)));
        foreach (object a in t.GetCustomAttributes(false))
        {
            Type at = a.GetType();
            Type arg = at.GetGenericArguments()[0];
            Console.WriteLine($"{at.Name} <{arg}>");
        }
        try
        {
            object[] open = t.GetCustomAttributes(
                typeof(TagAttribute<>), false);
            Console.WriteLine("open generic: " + open.Length);
        }
        catch (Exception e)
        {
            Console.WriteLine("open generic: " + e.GetType().Name);
        }
    }
}
