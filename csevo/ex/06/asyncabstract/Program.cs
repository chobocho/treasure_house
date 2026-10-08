// 슬라이드 p6-v5-asyncabstract — 몸체 없는 멤버와 async, C# 5.0
using System.Threading.Tasks;

interface IStore
{
    async Task<int> Get(string key);
}

abstract class Base
{
    public abstract async Task Save();
}

class App { static void Main() { } }
