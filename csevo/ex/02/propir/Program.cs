// 슬라이드 p2-v1-propir — 속성이 낳는 get_·set_ 메서드, C# 1.0
using System;
using System.Reflection;

class Person
{
    string name;
    public string Name
    {
        get { return name; }
        set { name = value; }
    }
    public int Age { get { return 30; } }
}

class App
{
    static void Main()
    {
        BindingFlags f = BindingFlags.Instance | BindingFlags.Public
            | BindingFlags.DeclaredOnly;
        MethodInfo[] ms = typeof(Person).GetMethods(f);
        string[] names = new string[ms.Length];
        for (int i = 0; i < ms.Length; i++)
            names[i] = ms[i].ReturnType.Name + " " + ms[i].Name
                + " special=" + ms[i].IsSpecialName;
        Array.Sort(names);
        foreach (string s in names) Console.WriteLine(s);

        PropertyInfo p = typeof(Person).GetProperty("Age");
        Console.WriteLine("Age: CanRead=" + p.CanRead
            + " CanWrite=" + p.CanWrite);
    }
}
