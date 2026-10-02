// 슬라이드 p5-v4-dyn-void — void 를 값으로 받으면, C# 4.0
using System;
using System.Collections.Generic;
using Microsoft.CSharp.RuntimeBinder;

class Program
{
    static void Main()
    {
        dynamic list = new List<int>();
        list.Add(1);
        list.Clear();                 // statement: fine
        Console.WriteLine(list.Count);
        try
        {
            var r = list.Clear();     // compiles: the result is dynamic
            Console.WriteLine(r);
        }
        catch (RuntimeBinderException e)
        {
            Console.WriteLine(e.Message);
        }
#if BAD
        var r2 = ((List<int>)list).Clear();
#endif
    }
}
