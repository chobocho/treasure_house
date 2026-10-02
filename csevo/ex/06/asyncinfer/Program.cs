// 슬라이드 p6-v5-infer — async 람다의 추론된 반환 형식, C# 5.0
using System;
using System.Threading.Tasks;

class App
{
    // T is inferred from the lambda's inferred return type.
    static T Call<T>(Func<T> f)
    {
        Console.WriteLine("T = " + Name(typeof(T)));
        return f();
    }

    static string Name(Type t)
    {
        if (!t.IsGenericType) return t.Name;
        return t.Name.Split('`')[0] + "<"
            + Name(t.GetGenericArguments()[0]) + ">";
    }

    static void Main()
    {
        Call(() => 42);
        Task<int> a = Call(async () => 42);
        Task b = Call(async () => { await Task.Yield(); });
        Task<string> c = Call(async () =>
        {
            await Task.Yield();
            return "done";
        });
        Console.WriteLine(a.Result + " " + c.Result);
        b.Wait();
    }
}
