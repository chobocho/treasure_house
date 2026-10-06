// 슬라이드 p14-v13-ar-new — new() 로 ref struct 를 만든다, C# 13.0
using System;

ref struct Counter
{
    public int N;
    public Counter() { N = 100; }
}

class App
{
    static int Make<T>(Func<T, int> read)
        where T : new(), allows ref struct
    {
        T t = new T();                 // a ref struct on the stack
        return read(t);
    }

    static int ViaActivator<T>(Func<T, int> read)
        where T : allows ref struct
        => read(Activator.CreateInstance<T>());

    static void Main()
    {
        Console.WriteLine(Make<Counter>(c => c.N));
        Console.WriteLine(Make<int>(i => i));
        Console.WriteLine(ViaActivator<Counter>(c => c.N));
    }
}
