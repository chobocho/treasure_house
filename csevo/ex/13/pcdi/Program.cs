// 슬라이드 p13-v12-pc-di — 의존성 주입의 상투 코드가 사라진다, C# 12.0
using System;
using System.Collections.Generic;

interface IClock { string Now(); }
interface IStore { void Save(string line); }
class FixedClock : IClock { public string Now() => "09:00"; }
class ListStore(List<string> lines) : IStore
{
    public void Save(string line) => lines.Add(line);
}

// before: two fields + a constructor that copies the parameters
class AuditOld
{
    private readonly IClock _clock;
    private readonly IStore _store;
    public AuditOld(IClock clock, IStore store)
    {
        _clock = clock; _store = store;
    }
    public void Log(string m) => _store.Save($"{_clock.Now()} {m}");
}

// C# 12: the parameters are the state
class Audit(IClock clock, IStore store)
{
    public void Log(string m) => store.Save($"{clock.Now()} {m}");
}

class App
{
    static void Main()
    {
        var lines = new List<string>();
        var store = new ListStore(lines);
        new AuditOld(new FixedClock(), store).Log("old");
        new Audit(new FixedClock(), store).Log("new");
        lines.ForEach(Console.WriteLine);
    }
}
