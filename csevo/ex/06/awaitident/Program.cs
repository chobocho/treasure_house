// 슬라이드 p6-v5-ident — await 는 문맥 키워드, C# 5.0
using System;
using System.Threading.Tasks;

class App
{
    // not async: await is just a name
    static int Twice(int await)
    {
        int async = 2;
        return await * async;
    }

    // async: await is an operator; the name is @await
    static async Task<int> Fetch()
    {
        int @await = await Task.FromResult(21);
        return Twice(@await);
    }

    static void Main()
    {
        Console.WriteLine(Twice(5));
        Console.WriteLine(Fetch().Result);
    }
}
