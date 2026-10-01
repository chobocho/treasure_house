// 슬라이드 p6-v5-asyncimpl — async 는 시그니처가 아니다, C# 5.0
using System;
using System.Threading.Tasks;

interface IStore
{
    Task<int> Get(string key);          // no async here
}

class Cached : IStore                   // not async: already known
{
    public Task<int> Get(string key) { return Task.FromResult(1); }
}

class Remote : IStore                   // async: awaits something
{
    public async Task<int> Get(string key)
    {
        await Task.Delay(1);
        return key.Length;
    }
}

class App
{
    static async Task<int> Sum(IStore s)
    {
        return await s.Get("a") + await s.Get("bcd");
    }

    static void Main()
    {
        Console.WriteLine("Cached " + Sum(new Cached()).Result);
        Console.WriteLine("Remote " + Sum(new Remote()).Result);
        Console.WriteLine("Remote.Get has a state machine? " +
            typeof(Remote).GetMethod("Get").IsDefined(
                typeof(System.Runtime.CompilerServices
                    .AsyncStateMachineAttribute), false));
    }
}
