// 슬라이드 p5-v4-dyn-genattr — 뒤 버전: 제네릭 특성에 dynamic, C# 11.0
using System;

class TagAttribute<T> : Attribute
{
    public override string ToString() { return typeof(T).Name; }
}

[Tag<object>]
class Ok { }

#if BAD
[Tag<dynamic>]
class Bad { }
#endif

class Program
{
    static void Main()
    {
        object[] a = typeof(Ok).GetCustomAttributes(false);
        Console.WriteLine(a[0]);
    }
}
