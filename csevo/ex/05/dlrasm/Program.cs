// 슬라이드 p5-v4-runtime — dynamic 을 받치는 형식들의 자리, C# 4.0
using System;
using System.Dynamic;
using System.Runtime.CompilerServices;
using Microsoft.CSharp.RuntimeBinder;

class Program
{
    static void Main()
    {
        Type[] types = {
            typeof(IDynamicMetaObjectProvider),
            typeof(DynamicMetaObject),
            typeof(ExpandoObject),
            typeof(DynamicObject),
            typeof(CallSite),
            typeof(CallSite<>),
            typeof(DynamicAttribute),
            typeof(Binder),
            typeof(RuntimeBinderException),
        };
        foreach (Type t in types)
        {
            Console.WriteLine("{0,-50} {1}", t.FullName,
                              t.Assembly.GetName().Name);
        }
    }
}
