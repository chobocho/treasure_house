// 슬라이드 p3-v2-variance — BCL 이 선언한 변성 쓰기, C# 2.0
using System;
using System.Collections.Generic;
using System.Reflection;

class App
{
    static void Main()
    {
        IEnumerable<object> e = new List<string>();
        Console.WriteLine(e is IEnumerable<object>);

        Type t = typeof(IEnumerable<>).GetGenericArguments()[0];
        GenericParameterAttributes v =
            t.GenericParameterAttributes
            & GenericParameterAttributes.VarianceMask;
        Console.WriteLine("IEnumerable<T>: T is " + v);
    }
}
