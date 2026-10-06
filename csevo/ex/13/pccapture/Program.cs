// 슬라이드 p13-v12-pc-capture — 포착된 매개변수는 숨은 필드, C# 12.0
using System;
using System.Reflection;

class Counter(int start)
{
    public int Next() => start++;
}

class App
{
    static void Main()
    {
        var flags = BindingFlags.Instance | BindingFlags.NonPublic;
        foreach (var f in typeof(Counter).GetFields(flags))
        {
            Console.WriteLine($"{f.Name} {f.FieldType.Name} "
                + $"{f.Attributes} readonly={f.IsInitOnly}");
            foreach (var a in f.GetCustomAttributesData())
                Console.WriteLine("  " + a.AttributeType.Name);
        }
        var c = new Counter(10);
        c.Next(); c.Next();
        var field = typeof(Counter).GetField("<start>P", flags);
        Console.WriteLine("after two Next(): " + field.GetValue(c));
    }
}
