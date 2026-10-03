// 슬라이드 p11-v10-st-generic — new T() 와 Activator, C# 10.0
using System;

struct Seed
{
    public int Value;
    public Seed() { Value = 7; }
}

class App
{
    static T ByNew<T>() where T : new() => new T();
    static T ByStruct<T>() where T : struct => new T();
    static T ByDefault<T>() => default(T);

    static void Main()
    {
        Console.WriteLine("where T : new()  " + ByNew<Seed>().Value);
        Console.WriteLine("where T : struct " + ByStruct<Seed>().Value);
        Console.WriteLine("default(T)       "
            + ByDefault<Seed>().Value);
        Console.WriteLine("Activator        "
            + ((Seed)Activator.CreateInstance(typeof(Seed))).Value);
    }
}
