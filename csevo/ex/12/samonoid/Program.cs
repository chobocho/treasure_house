// 슬라이드 p12-v11-static-abstract — static abstract 멤버, C# 11.0
using System;

public interface IMonoid<TSelf> where TSelf : IMonoid<TSelf>
{
    public static abstract TSelf operator +(TSelf a, TSelf b);
    public static abstract TSelf Zero { get; }
}

public struct MyInt : IMonoid<MyInt>
{
    int value;
    public MyInt(int i) => value = i;
    public static MyInt operator +(MyInt a, MyInt b) =>
        new MyInt(a.value + b.value);
    public static MyInt Zero => new MyInt(0);
    public override string ToString() => "MyInt " + value;
}

class App
{
    static T AddAll<T>(params T[] elements) where T : IMonoid<T>
    {
        T result = T.Zero;
        foreach (var element in elements)
            result += element;
        return result;
    }

    static void Main()
    {
        MyInt sum =
            AddAll<MyInt>(new MyInt(3), new MyInt(4), new MyInt(5));
        Console.WriteLine(sum);
        Console.WriteLine(AddAll<MyInt>());
    }
}
