// 슬라이드 p4-v3-anon-class — 컴파일러가 만든 클래스, C# 3.0
using System;
using System.Reflection;
using System.Runtime.CompilerServices;

class App
{
    static void Main()
    {
        var p = new { Name = "Ann", Age = 31 };
        Type t = p.GetType();
        Console.WriteLine("class: " + t.IsClass
            + ", base: " + t.BaseType);
        Console.WriteLine("sealed: " + t.IsSealed
            + ", public: " + t.IsPublic);
        Console.WriteLine("[CompilerGenerated]: "
            + t.IsDefined(typeof(CompilerGeneratedAttribute), false));
        Console.WriteLine("name is a C# identifier: "
            + (char.IsLetter(t.Name[0]) || t.Name[0] == '_'));
        foreach (PropertyInfo pi in t.GetProperties())
            Console.WriteLine("property " + pi.PropertyType.Name + " "
                + pi.Name + ", CanWrite=" + pi.CanWrite);
        foreach (FieldInfo f in t.GetFields(
            BindingFlags.NonPublic | BindingFlags.Instance))
            Console.WriteLine("private field " + f.FieldType.Name
                + ", readonly=" + f.IsInitOnly);
        Console.WriteLine("generic definition behind it: "
            + t.IsGenericType);
    }
}
