// 슬라이드 p12-v11-genattr-history — 표준 초안의 예를 옮긴 것, C# 11.0
using System;

public class B : Attribute { }
public class C<T> : B { }      // standard: "Error - generic cannot be
                               // an attribute"
[C<int>]
class App
{
    static void Main()
    {
        Console.WriteLine(typeof(App).GetCustomAttributes(false)[0]);
    }
}
