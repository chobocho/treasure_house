// 슬라이드 p10-v9-varstatic — 인터페이스 static 멤버와 변성, C# 9.0
using System;
using System.Threading.Tasks;

public interface I<out T>
{
    static Task<T> F = Task.FromResult(default(T));    // field: ok
    static Task<T> P => Task.FromResult(default(T));   // C# 9
    static Task<T> M() => Task.FromResult(default(T)); // C# 9
    static T Echo(T t) => t;                           // T as input
}

class App
{
    static void Main()
    {
        Console.WriteLine(I<string>.F.Result ?? "null");
        Console.WriteLine(I<int>.P.Result + " " + I<int>.M().Result);
        Console.WriteLine(I<string>.Echo("in"));
        I<object> o = (I<string>)null;     // out T still works
        Console.WriteLine(o == null);
    }
}
