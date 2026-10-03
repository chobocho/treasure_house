// 슬라이드 p12-v11-genattr-multi — AllowMultiple 과 형식 인수, C# 11.0
using System;

[AttributeUsage(AttributeTargets.Class, AllowMultiple = false)]
class OneAttribute<T> : Attribute { }

[One<int>]
class Ok { }

#if TWO
[One<int>, One<string>]
class Twice { }
#endif

class App
{
    static void Main()
    {
        var u = (AttributeUsageAttribute)Attribute.GetCustomAttribute(
            typeof(OneAttribute<string>),
            typeof(AttributeUsageAttribute));
        Console.WriteLine("AllowMultiple = " + u.AllowMultiple);
        Console.WriteLine(typeof(Ok).GetCustomAttributes(false)[0]);
    }
}
