// 슬라이드 p5-v4-dyn-access — 바인더는 접근성을 지킨다, C# 4.0
using System;
using Microsoft.CSharp.RuntimeBinder;

class Factory
{
    class Hidden                      // private nested type
    {
        public string Name = "hidden";
    }

    public static object Make() { return new Hidden(); }
}

class Program
{
    static void Main()
    {
        dynamic anon = new { Name = "anon" };
        Console.WriteLine(anon.Name);
        Console.WriteLine("anonymous type public? " +
                          anon.GetType().IsPublic);

        dynamic h = Factory.Make();
        Console.WriteLine("runtime type: " + h.GetType().Name);
        try
        {
            Console.WriteLine(h.Name);
        }
        catch (RuntimeBinderException e)
        {
            Console.WriteLine(e.Message);
        }
    }
}
